import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class StorageStack extends cdk.Stack {
  public readonly evidenceBucket: s3.Bucket;
  public readonly configBackupBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Evidence Bucket for image storage
    this.evidenceBucket = new s3.Bucket(this, 'EvidenceBucket', {
      bucketName: `${id.toLowerCase()}-evidence-${this.account}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      lifecycleRules: [
        {
          id: 'DeleteOldVersions',
          noncurrentVersionExpiration: cdk.Duration.days(90),
          enabled: true,
        },
        {
          id: 'TransitionToIA',
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(90),
            },
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(180),
            },
          ],
          enabled: true,
        },
      ],
      cors: [
        {
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.PUT,
            s3.HttpMethods.POST,
          ],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3000,
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Note: Tenant isolation will be enforced at the application layer
    // S3 bucket policies don't support dynamic tenant-based conditions effectively
    // The Lambda functions will enforce tenant isolation when accessing objects

    // Config Backup Bucket
    this.configBackupBucket = new s3.Bucket(this, 'ConfigBackupBucket', {
      bucketName: `${id.toLowerCase()}-config-backup-${this.account}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      lifecycleRules: [
        {
          id: 'DeleteOldBackups',
          expiration: cdk.Duration.days(365),
          noncurrentVersionExpiration: cdk.Duration.days(30),
          enabled: true,
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Outputs
    new cdk.CfnOutput(this, 'EvidenceBucketName', {
      value: this.evidenceBucket.bucketName,
      description: 'S3 Bucket for image evidence',
      exportName: `${id}-EvidenceBucketName`,
    });

    new cdk.CfnOutput(this, 'EvidenceBucketArn', {
      value: this.evidenceBucket.bucketArn,
      description: 'S3 Bucket ARN for image evidence',
      exportName: `${id}-EvidenceBucketArn`,
    });

    new cdk.CfnOutput(this, 'ConfigBackupBucketName', {
      value: this.configBackupBucket.bucketName,
      description: 'S3 Bucket for configuration backups',
      exportName: `${id}-ConfigBackupBucketName`,
    });

    // Store configuration in SSM Parameter Store
    new cdk.aws_ssm.StringParameter(this, 'EvidenceBucketNameParameter', {
      parameterName: '/app/s3/evidence-bucket',
      stringValue: this.evidenceBucket.bucketName,
      description: 'S3 Bucket for image evidence',
    });

    new cdk.aws_ssm.StringParameter(this, 'ConfigBackupBucketNameParameter', {
      parameterName: '/app/s3/config-backup-bucket',
      stringValue: this.configBackupBucket.bucketName,
      description: 'S3 Bucket for configuration backups',
    });
  }
}
