import { useEffect, useRef } from 'react';

/**
 * Custom hook que ejecuta un callback una sola vez en el montaje del componente.
 * Previene la doble ejecución causada por React Strict Mode en desarrollo.
 *
 * En desarrollo:
 * - React Strict Mode ejecuta intentionalmente los effects dos veces para detectar efectos impuros
 * - Este hook usa useRef para rastrear la ejecución y garantizar que el callback se ejecute una sola vez
 *
 * En producción:
 * - Funciona de forma normal sin afectar el comportamiento
 *
 * @param callback Función a ejecutar en el montaje (puede ser async)
 *
 * @example
 * ```tsx
 * const MyComponent = () => {
 *   useFetchOnce(async () => {
 *     const data = await api.fetch();
 *     setData(data);
 *   });
 *   return <div>{data}</div>;
 * };
 * ```
 */
export const useFetchOnce = (callback: () => void | Promise<void>) => {
  const hasRun = useRef(false);

  useEffect(() => {
    // Guardia: si ya se ejecutó, no ejecutar de nuevo
    if (!hasRun.current) {
      hasRun.current = true;
      callback();
    }
  }, []); // Dependencias vacías: ejecutar solo en montaje
};
