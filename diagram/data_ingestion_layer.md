### Internal Architecture: Resilient Data Ingestion Layer

```mermaid
graph TD
    subgraph "External Data Sources"
        A["Satellite Imagery Provider (Batch Uploads)"]
        B["Live Drone Feeds (Video Stream)"]
        C["Social Media & News APIs (Events)"]
        D["Help Center (Audio Stream via STT)"]
        E["Rescue Team Mobile Apps (API Calls)"]
    end

    subgraph "1. Specialized Ingestion Endpoints"
        S3_Ingest["S3 Bucket (for file uploads)"]
        KVS["Amazon Kinesis Video Streams"]
        EventBridge["Amazon EventBridge (Scheduler/Webhook)"]
        KDS["Amazon Kinesis Data Streams"]
        APIGW["Amazon API Gateway (REST API)"]
    end

    subgraph "2. The Central Buffer (Decoupling)"
        SQS["<b>Amazon SQS Queue</b><br><i>Acts as a resilient buffer.<br>Stores messages if downstream is slow.</i>"]
        DLQ["<b>SQS Dead-Letter Queue</b><br><i>Catches and holds messages that fail processing.</i>"]
        SQS -- "On failure" --> DLQ
    end

    subgraph "3. Raw Data Persistence"
        Ingest_Lambda["<b>Ingestion Lambda</b><br><i>Triggered by SQS.<br>Writes raw data to S3.</i>"]
        S3_Raw["<b>S3 Data Lake (Raw Zone)</b><br><i>Permanent, immutable storage.</i>"]
    end

    %% Connections
    A -- "Uploads to" --> S3_Ingest
    B -- "Streams to" --> KVS
    C -- "Sends events to" --> EventBridge
    D -- "Pushes data to" --> KDS
    E -- "Sends requests to" --> APIGW
    
    %% Funneling to the Buffer
    S3_Ingest -- "Triggers event notification to" --> SQS
    KVS -- "Triggers Lambda which sends message to" --> SQS
    EventBridge -- "Forwards events to" --> SQS
    KDS -- "Triggers Lambda which sends message to" --> SQS
    APIGW -- "Proxies requests to Lambda which sends message to" --> SQS
    
    %% Processing from the Buffer
    SQS -- "Triggers" --> Ingest_Lambda
    Ingest_Lambda -- "Writes raw object to" --> S3_Raw
    S3_Raw -- "Notifies next system (ETL)" --> ...
```

-----

### How It Works & Communicates

#### 1\. Specialized Ingestion Endpoints

Each data source interacts with an AWS service designed specifically for its data type.

  * **Satellite Imagery:** A new satellite image is a large file uploaded periodically. The best entry point is directly to an **S3 bucket**. This is simple and cost-effective.
  * **Live Drone Feeds:** This is a continuous video stream. **Amazon Kinesis Video Streams** is built to handle this, allowing for real-time processing and storage.
  * **Social Media & News:** This data often comes as discrete events. **Amazon EventBridge** is perfect as it can be configured to poll an API on a schedule (e.g., every minute) or act as a direct webhook target.
  * **Help Center Data:** After your STT (Speech-to-Text) model transcribes audio, you have a high-throughput stream of text data. **Amazon Kinesis Data Streams** is designed to ingest massive volumes of streaming data records like this.
  * **Rescue Team Apps:** A rescuer in the field sends a specific update, like a form submission. This is a classic transactional request, perfectly handled by an **Amazon API Gateway** endpoint.

#### 2\. The Central Buffer (Decoupling) 🌪️

This is the most critical part for resilience. After each specialized endpoint receives data, it doesn't immediately try to process it. Instead, it sends a small message to a central **Amazon SQS (Simple Queue Service) queue**.

  * **The Message:** This message contains either the data itself (if small) or a pointer to where the data is stored (e.g., the S3 path for a satellite image).
  * **Why is this so important?** The SQS queue acts as a shock absorber. If the next part of your system (the ETL pipeline) is slow, overloaded, or even temporarily offline, the data doesn't get lost. It simply waits safely in the queue. This **decouples** your ingestion from your processing, ensuring you never miss an update.
  * **Error Handling:** We configure a **Dead-Letter Queue (DLQ)**. If a message fails to be processed multiple times, SQS automatically moves it to the DLQ. This isolates the problematic data so it doesn't block the rest of the pipeline and allows engineers to inspect and fix it later.

#### 3\. Raw Data Persistence 💾

The final step of this layer is to create a permanent record.

  * An **AWS Lambda function** is subscribed to the SQS queue. Whenever new messages are available, the Lambda is automatically triggered.
  * Its only job is to read the message, retrieve the full data payload, and write it as a raw, timestamped file into the **Raw Zone of your S3 Data Lake**.
  * **Communication with Next System:** Once the file is written to S3, it automatically sends out an event notification (e.g., "new object created"). This event will trigger the next subsystem in our design: the **Data Lake & ETL Pipeline**.