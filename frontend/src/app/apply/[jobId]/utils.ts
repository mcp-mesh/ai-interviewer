// Utility function to convert date from "MM/YYYY" or "YYYY" to "YYYY-MM" format for HTML input type="month"
export function convertDateFormat(dateStr: string): string {
  if (!dateStr || dateStr.toLowerCase() === 'present') return ''
  
  // Handle "MM/YYYY" format
  if (dateStr.includes('/')) {
    const [month, year] = dateStr.split('/')
    return `${year}-${month.padStart(2, '0')}`
  }
  
  // Handle "YYYY" format - assume January
  if (dateStr.length === 4) {
    return `${dateStr}-01`
  }
  
  return ''
}