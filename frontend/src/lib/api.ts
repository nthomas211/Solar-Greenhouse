export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders = {
        "Content-Type": "application/json"
    }

    const response = await fetch(url, {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        }
    })

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error (`API Error (${response.status}): ${errorData.detail || response.statusText}`)
    }
    return await response.json()
}

export async function fetchSimulation(area: string | number, materials: string[], location: string) {
    return fetchAPI("/simulate", {
        method: "GET",
        body: JSON.stringify({
            area: typeof area === "string" ? Number.parseFloat(area) || 0 : area,
            materials,
            location,
        })
    })
}