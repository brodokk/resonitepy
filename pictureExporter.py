from datetime import datetime
from neos import client, classes
import asyncio
from os import path
import json
from getpass import getpass


c = client.Client()


async def printContents(path="Inventory", indentation=0):
    node = await c.getInventoryPath(path)
    for item in node:
        print(f"{'    '*indentation}{item.name} - {item.recordType.value}")
        if isinstance(item, classes.NeosDirectory):
            await printContents(path + "\\" + item.name, indentation + 1)


async def main():
    have_auth = False
    try:
        c.loadToken()
        have_auth = True
    except classes.NoTokenError:
        pass

    if not have_auth:
        print(
            "Please provide your Neos Login Details."
            "\n This data goes to the neos server, to get a token."
            "\n While typing your password, no input will appear. This is intentional.\n"
        )
        email = input("Username / Email: ")
        password = getpass()
        deets = classes.LoginDetails(email, password)
        if not await c.login(deets):
            print("it seems that that login was invalid :(")
            exit(-1)
        data = input(
            f"Would you like to store your token to your harddrive?"
            f"this token will expire naturally in {(c.expirey - datetime.utcnow()).days} days"
        )
        if data.lower() in ["true", "1", "t", "y", "yes", "yeah", "yup"]:
            print("saving token..")
            c.saveToken()

    # await printContents()
    # todo: more stuff here


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
