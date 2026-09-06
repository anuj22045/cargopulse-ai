const API_BASE_URL = "http://127.0.0.1:8000";

export async function apiClient(
    endpoint: string,
    options?: RequestInit
) {
    try {
    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {})
        }
        }
    );

    if (!response.ok) {
        let message = `API request failed: ${response.status}`;

        try {
        const errorData = await response.json();

        if (errorData.detail) {
            message = errorData.detail;
        }
        } catch {
        // Ignore invalid error response
        }

        throw new Error(message);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
    } catch (error) {
    if (error instanceof Error) {
        throw error;
    }

    throw new Error("Unable to connect to CargoPulse API");
    }
}   