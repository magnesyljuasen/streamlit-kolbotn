import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['Yzd6FDQ6hJy7', 'khpLp3qR', 'GRUNNVARME123']).generate()
print(hashed_passwords)

    