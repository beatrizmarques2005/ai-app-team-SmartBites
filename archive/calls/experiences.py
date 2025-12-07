supabase = create_client(URL, ANON_KEY)

auth = supabase.auth.sign_in_with_password({
  "email": email,
  "password": password
})