export function isoDate(date) {
  return date.toISOString().slice(0, 10);
}

export function localDateTimeInputValue(value) {
  const date = value ? new Date(value) : new Date();
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

export function toApiDateTime(localValue) {
  return new Date(localValue).toISOString();
}

export function displayDateTime(value) {
  return new Date(value).toLocaleString();
}
