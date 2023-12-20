import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['Jh4Lp9qR', 'khpLp3qR', 'GRUNNVARME123']).generate()
print(hashed_passwords)

    