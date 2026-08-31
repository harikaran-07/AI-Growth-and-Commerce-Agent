/**
 * Product name sanitization utility.
 * Removes Markdown formatting, HTML, and extra whitespace from product names.
 * 
 * Example:
 *   sanitizeProductName("**Sony WH-1000XM5**") => "Sony WH-1000XM5"
 *   sanitizeProductName("## Samsung Galaxy S25") => "Samsung Galaxy S25"
 *   sanitizeProductName("`iPhone 15 Pro`") => "iPhone 15 Pro"
 */
export function sanitizeProductName(name: string | null | undefined): string {
  if (!name) return '';
  
  let clean = String(name);
  
  // Remove Markdown bold markers
  clean = clean.replace(/\*\*\*/g, '');
  clean = clean.replace(/\*\*/g, '');
  
  // Remove Markdown italic markers
  clean = clean.replace(/(?<!\*)\*(?!\*)/g, '');
  
  // Remove Markdown headers
  clean = clean.replace(/^#{1,6}\s+/gm, '');
  
  // Remove backticks
  clean = clean.replace(/`/g, '');
  
  // Remove HTML tags
  clean = clean.replace(/<[^>]+>/g, '');
  
  // Remove escaped HTML entities
  clean = clean.replace(/&amp;/g, '&');
  clean = clean.replace(/&lt;/g, '<');
  clean = clean.replace(/&gt;/g, '>');
  clean = clean.replace(/&quot;/g, '"');
  clean = clean.replace(/&#39;/g, "'");
  
  // Remove JSON formatting artifacts
  clean = clean.replace(/^\s*\{[\s\S]*"name":\s*"/, '');
  clean = clean.replace(/"\s*\}\s*$/, '');
  
  // Clean up repeated formatting characters
  clean = clean.replace(/[_~]{2,}/g, '');
  
  // Trim whitespace
  clean = clean.trim();
  
  return clean;
}

/**
 * Sanitize any text for display (remove Markdown, HTML, technical formatting).
 * Less aggressive than sanitizeProductName — preserves some formatting.
 */
export function sanitizeDisplayText(text: string | null | undefined): string {
  if (!text) return '';
  
  let clean = String(text);
  
  // Remove HTML tags
  clean = clean.replace(/<[^>]+>/g, '');
  
  // Remove code blocks
  clean = clean.replace(/```[\s\S]*?```/g, '[code block removed]');
  
  // Remove inline code
  clean = clean.replace(/`([^`]+)`/g, '$1');
  
  // Clean up [object Object] artifacts
  clean = clean.replace(/\[object Object\]/g, '');
  
  // Clean up undefined/null/NaN artifacts
  clean = clean.replace(/\bundefined\b/g, '');
  clean = clean.replace(/\bnull\b/g, '');
  clean = clean.replace(/\bNaN\b/g, '0');
  
  // Trim
  clean = clean.trim();
  
  return clean || 'No content available';
}

/**
 * Format a price value for Indian Rupees display.
 */
export function formatPrice(price: number | null | undefined): string {
  if (price == null || isNaN(price)) return '₹0';
  return `₹${Number(price).toLocaleString('en-IN')}`;
}

/**
 * Format a number for display.
 */
export function formatNumber(num: number | null | undefined): string {
  if (num == null || isNaN(num)) return '0';
  return Number(num).toLocaleString('en-IN');
}
