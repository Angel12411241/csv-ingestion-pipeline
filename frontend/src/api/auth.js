import client from "./client";

export async function register(email, password) {
  const { data } = await client.post("/register", { email, password });
  return data;
}

/** OAuth2 password flow: the backend expects form fields `username` and `password`. */
export async function login(email, password) {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await client.post("/login", form);
  return data;
}
