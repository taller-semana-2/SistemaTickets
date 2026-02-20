/**
 * Helpers puros de formateo de fecha.
 * Reutilizables en cualquier componente sin dependencia de React.
 */

const DATE_FORMAT_OPTIONS: Intl.DateTimeFormatOptions = {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
};

const DATE_FORMATTER = new Intl.DateTimeFormat('es-ES', DATE_FORMAT_OPTIONS);

/**
 * Formatea una cadena ISO 8601 a un formato legible en español.
 *
 * @param isoString - Fecha en formato ISO 8601
 * @returns Fecha legible o fallback si inválida
 */
export const formatDate = (isoString: string): string => {
  if (!isoString) return 'Sin fecha';

  const date = new Date(isoString);

  if (isNaN(date.getTime())) return 'Fecha inválida';

  return DATE_FORMATTER.format(date);
};

/**
 * Ordena un array por campo de fecha ISO 8601 en orden ascendente.
 * No muta el array original.
 */
export const sortByDateAsc = <T extends { [K in keyof T]: unknown }>(
  items: T[],
  dateKey: keyof T & string,
): T[] =>
  [...items].sort(
    (a, b) => new Date(String(a[dateKey])).getTime() - new Date(String(b[dateKey])).getTime(),
  );
