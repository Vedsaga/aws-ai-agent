/**
 * Popup Utilities
 * Functions for creating detailed map popups with enhanced styling
 */

import mapboxgl from 'mapbox-gl';
import { getCategoryColors } from './category-config';
import { formatDate, type Incident } from './map-utils';

/**
 * Create a detailed popup with category header, structured data, and images
 */
export function createDetailedPopup(incident: Incident): mapboxgl.Popup {
  const popupContent = document.createElement('div');
  popupContent.className = 'popup-container';
  popupContent.style.cssText = `
    max-width: 400px;
    max-height: 500px;
    overflow-y: auto;
  `;

  // Extract category
  const category = 
    incident.structured_data?.entity_agent?.category ||
    incident.structured_data?.category ||
    'default';
  
  const colors = getCategoryColors(category);

  // Category Header
  const header = document.createElement('div');
  header.style.cssText = `
    background: ${colors.bg};
    color: white;
    padding: 12px 16px;
    margin: -12px -16px 12px -16px;
    border-radius: 8px 8px 0 0;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 16px;
  `;
  header.innerHTML = `
    <span style="font-size: 24px;">${colors.icon}</span>
    <span>${category.replace(/_/g, ' ').toUpperCase()}</span>
  `;
  popupContent.appendChild(header);

  // Original Report Section
  const reportSection = createReportSection(incident);
  popupContent.appendChild(reportSection);

  // Structured Data Section
  const structuredSection = createStructuredDataSection(incident);
  popupContent.appendChild(structuredSection);

  // Image Gallery
  if (incident.images && incident.images.length > 0) {
    const imageGallery = createImageGallery(incident);
    popupContent.appendChild(imageGallery);
  }

  // Action Buttons
  const actionButtons = createActionButtons(incident);
  popupContent.appendChild(actionButtons);

  // Timestamp footer
  const footer = document.createElement('div');
  footer.style.cssText = `
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    text-align: right;
  `;
  footer.textContent = formatDate(incident.created_at);
  popupContent.appendChild(footer);

  return new mapboxgl.Popup({ 
    offset: 25,
    maxWidth: '400px',
    className: 'custom-popup'
  }).setDOMContent(popupContent);
}

/**
 * Create the original report section
 */
function createReportSection(incident: Incident): HTMLElement {
  const section = document.createElement('div');
  section.style.cssText = `
    margin-bottom: 16px;
  `;

  const heading = document.createElement('h4');
  heading.style.cssText = `
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.9);
  `;
  heading.textContent = 'Report';
  section.appendChild(heading);

  const text = document.createElement('p');
  text.style.cssText = `
    font-size: 13px;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  `;
  text.textContent = incident.raw_text;
  section.appendChild(text);

  return section;
}

/**
 * Create the structured data section with agent outputs
 */
function createStructuredDataSection(incident: Incident): HTMLElement {
  const section = document.createElement('div');
  section.style.cssText = `
    margin-bottom: 16px;
  `;

  const heading = document.createElement('h4');
  heading.style.cssText = `
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.9);
  `;
  heading.textContent = 'Extracted Data';
  section.appendChild(heading);

  if (!incident.structured_data || Object.keys(incident.structured_data).length === 0) {
    const noData = document.createElement('p');
    noData.style.cssText = `
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      font-style: italic;
    `;
    noData.textContent = 'No structured data available';
    section.appendChild(noData);
    return section;
  }

  // Loop through each agent's output
  Object.entries(incident.structured_data).forEach(([agentName, agentData]) => {
    const agentCard = document.createElement('div');
    agentCard.style.cssText = `
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      padding: 10px;
      margin-bottom: 8px;
    `;

    // Agent name heading
    const agentHeading = document.createElement('div');
    agentHeading.style.cssText = `
      font-size: 12px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 6px;
      text-transform: capitalize;
    `;
    agentHeading.textContent = agentName.replace(/_/g, ' ');
    agentCard.appendChild(agentHeading);

    // Agent data key-value pairs
    if (typeof agentData === 'object' && agentData !== null) {
      const dataList = document.createElement('div');
      dataList.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 4px;
      `;

      Object.entries(agentData).forEach(([key, value]) => {
        const item = document.createElement('div');
        item.style.cssText = `
          font-size: 12px;
          display: flex;
          gap: 6px;
        `;

        const keySpan = document.createElement('span');
        keySpan.style.cssText = `
          color: rgba(255, 255, 255, 0.6);
          min-width: 80px;
        `;
        keySpan.textContent = `${key}:`;

        const valueSpan = document.createElement('span');
        valueSpan.style.cssText = `
          color: rgba(255, 255, 255, 0.9);
          flex: 1;
        `;
        valueSpan.textContent = formatValue(value);

        item.appendChild(keySpan);
        item.appendChild(valueSpan);
        dataList.appendChild(item);
      });

      agentCard.appendChild(dataList);
    } else {
      const simpleValue = document.createElement('div');
      simpleValue.style.cssText = `
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
      `;
      simpleValue.textContent = String(agentData);
      agentCard.appendChild(simpleValue);
    }

    section.appendChild(agentCard);
  });

  return section;
}

/**
 * Create image gallery section
 */
function createImageGallery(incident: Incident): HTMLElement {
  const section = document.createElement('div');
  section.style.cssText = `
    margin-bottom: 16px;
  `;

  const heading = document.createElement('h4');
  heading.style.cssText = `
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.9);
  `;
  heading.textContent = 'Images';
  section.appendChild(heading);

  const gallery = document.createElement('div');
  gallery.style.cssText = `
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  `;

  incident.images!.forEach((imageUrl) => {
    const imgContainer = document.createElement('div');
    imgContainer.style.cssText = `
      aspect-ratio: 1;
      overflow: hidden;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid rgba(255, 255, 255, 0.1);
      transition: transform 0.2s ease;
    `;
    imgContainer.onmouseover = () => {
      imgContainer.style.transform = 'scale(1.05)';
    };
    imgContainer.onmouseout = () => {
      imgContainer.style.transform = 'scale(1)';
    };

    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = 'Incident evidence';
    img.style.cssText = `
      width: 100%;
      height: 100%;
      object-fit: cover;
    `;
    img.onclick = () => window.open(imageUrl, '_blank');

    imgContainer.appendChild(img);
    gallery.appendChild(imgContainer);
  });

  section.appendChild(gallery);
  return section;
}

/**
 * Create action buttons section
 */
function createActionButtons(incident: Incident): HTMLElement {
  const section = document.createElement('div');
  section.style.cssText = `
    display: flex;
    gap: 8px;
    margin-top: 16px;
  `;

  const viewDetailsBtn = document.createElement('button');
  viewDetailsBtn.style.cssText = `
    flex: 1;
    background: #3B82F6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s ease;
  `;
  viewDetailsBtn.textContent = 'View Full Details';
  viewDetailsBtn.onmouseover = () => {
    viewDetailsBtn.style.background = '#2563EB';
  };
  viewDetailsBtn.onmouseout = () => {
    viewDetailsBtn.style.background = '#3B82F6';
  };
  viewDetailsBtn.onclick = () => {
    window.location.href = `/manage/${incident.domain_id}?incident=${incident.id}`;
  };

  section.appendChild(viewDetailsBtn);
  return section;
}

/**
 * Format value for display
 */
function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  
  return String(value);
}
