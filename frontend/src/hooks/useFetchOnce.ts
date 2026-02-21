import { useEffect } from 'react';

/**
 * Custom hook que ejecuta una función de fetch con AbortController y dependencias vacías.
 *
 * **El patrón correcto:**
 * - Dependencias vacías: el effect solo corre en mount (no en cada render con nuevas lambdas)
 * - StrictMode aún cancela requests en-flight vía cleanup
 * - Las lambdas inline que pasas NO causan re-ejecuciones
 *
 * **Cómo funciona:**
 * 1. Componente monta → effect corre → request 1 inicia
 * 2. StrictMode desmonta/remonta → cleanup aborta request 1 → request 2 inicia
 * 3. Componente se actualiza → effect NO corre (deps = [])
 * 4. En producción sin StrictMode → solo request 1 completa
 *
 * @param fetchFn Función async que recibe AbortSignal y retorna Promise<T>
 * @param onSuccess Callback que se ejecuta al completar exitosamente
 * @param onError Callback que se ejecuta si hay error (excluye AbortError)
 *
 * @example
 * ```tsx
 * const MyComponent = () => {
 *   const [data, setData] = useState(null);
 *   const [error, setError] = useState(null);
 *
 *   useFetch(
 *     (signal) => ticketApi.getTickets(signal),
 *     (tickets) => setData(tickets),
 *     (err) => setError(err)
 *   );
 *
 *   return <div>{data?.length} tickets</div>;
 * };
 * ```
 */
export const useFetch = <T,>(
  fetchFn: (signal: AbortSignal) => Promise<T>,
  onSuccess: (data: T) => void,
  onError?: (error: Error) => void
) => {
  useEffect(() => {
    const controller = new AbortController();

    fetchFn(controller.signal)
      .then((data) => {
        onSuccess(data);
      })
      .catch((error: Error) => {
        // Ignorar AbortError (cancelación intencional de requests)
        if (error.name !== 'AbortError') {
          onError?.(error);
        }
      });

    // Cleanup: cancelar requests en-flight
    // En StrictMode: cancela con la primera ejecución del effect
    // En producción: solo se ejecuta si el component se desmonta antes de completar
    return () => controller.abort();

    // ⚠️ IMPORTANTE: deps = [] para evitar re-ejecuciones innecesarias
    // Las lambdas inline en los componentes NO causan que el effect corra de nuevo
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
};

/**
 * Hook alternativo simple para casos onde no necesitas manejar errores.
 * Mantiene compatibilidad con código anterior.
 *
 * @deprecated Usa `useFetch` directamente para mejor control
 */
export const useFetchOnce = (callback: () => void | Promise<void>) => {
  useFetch(
    (signal) => Promise.resolve(callback()),
    () => {},
    () => {}
  );
};
