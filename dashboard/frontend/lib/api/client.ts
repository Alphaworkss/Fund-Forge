let cachedBaseUrl: string | null = process.env.NEXT_PUBLIC_API_URL || null;
const CANDIDATE_PORTS = [8000, 8001];

export async function fetchApi<T>(path: string, options?: RequestInit, timeoutMs = 3500): Promise<T> {
  const candidateBases = cachedBaseUrl
    ? [cachedBaseUrl]
    : CANDIDATE_PORTS.map((port) => `http://localhost:${port}`);

  let lastError: any = null;

  for (const baseUrl of candidateBases) {
    const url = `${baseUrl}/api${path}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`API error (${res.status}): ${errorText || res.statusText}`);
      }

      cachedBaseUrl = baseUrl;
      return await res.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      lastError = err;
      if (candidateBases.length > 1) {
        console.warn(`Attempt at ${url} failed, trying fallback backend...`);
      }
    }
  }

  console.error(`All API endpoints failed for path ${path}:`, lastError);
  throw lastError || new Error(`Failed to connect to backend service. Make sure FastAPI server is running on port 8000 or 8001.`);
}


