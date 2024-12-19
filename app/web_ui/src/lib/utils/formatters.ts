export function formatDate(dateString: string | undefined): string {
  if (!dateString) {
    return "Unknown"
  }
  const date = new Date(dateString)
  const time_ago = Date.now() - date.getTime()
  if (time_ago < 1000 * 60) {
    return "just now"
  }
  if (time_ago < 1000 * 60 * 2) {
    return "1 minute ago"
  }
  if (time_ago < 1000 * 60 * 60) {
    return `${Math.floor(time_ago / (1000 * 60))} minutes ago`
  }

  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }

  const formattedDate = date.toLocaleString(undefined, options)
  // Helps on line breaks with CA/US locales
  return formattedDate
    .replace(" AM", "am")
    .replace(" PM", "pm")
    .replace(",", "")
}
