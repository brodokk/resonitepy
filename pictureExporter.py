import asyncio
from datetime import datetime
from getpass import getpass

from neos import classes, client, exceptions

c = client.Client()


async def printContents(node: classes.NeosDirectory, indentation=0):
    for item in await c.getDirectory(node):
        print(f"{'    '*indentation}{item.name} - {item.recordType.value}")
        if isinstance(item, classes.NeosDirectory):
            await printContents(item, indentation + 1)
        if isinstance(item, classes.NeosLink):
            dir = await c.resolveLink(item)
            await printContents(dir, indentation + 1)


async def main():
    have_auth = False
    try:
        c.loadToken()
        have_auth = True
    except exceptions.NoTokenError:
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

    await printContents(await c.resolveLink(next(x for x in await c.getInventory() if x.name == "Essential Tools")))
    # todo: more stuff here


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
