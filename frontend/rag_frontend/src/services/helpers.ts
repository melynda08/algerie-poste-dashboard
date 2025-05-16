export const getAuthHeaders = (skipContentType = false) => {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Authorization token is missing");
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };

  if (!skipContentType) {
    headers["Content-Type"] = "application/json";
  }

  return headers;
};