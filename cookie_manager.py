import browser_cookie3

def get_cookies():
    try:
        print("Loading Chrome cookies...")

        cookies = browser_cookie3.chrome()

        print("Cookies loaded:", len(cookies))

        return cookies

    except Exception as e:
        print("COOKIE ERROR:")
        print(e)
        return None