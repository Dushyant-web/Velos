function authFetch(url, options = {}) {
    const token = localStorage.getItem("token");

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "Authorization": token ? `Bearer ${token}` : "",
            "Content-Type": options.headers?.["Content-Type"] || "application/json"
        }
    });
}