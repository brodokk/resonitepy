import asyncio
from asyncio.tasks import Task
from datetime import datetime
from getpass import getpass
from typing import List
from collections import Counter
from neos import classes, client, exceptions

c = client.Client()


async def printContents(
    node: classes.NeosDirectory, indentation=0, exclude: List[str] = list()
) -> List[classes.NeosObject]:
    objects = []
    tasks: List[Task] = []
    for item in await c.getDirectory(node):
        if isinstance(item, classes.NeosObject):
            objects.append(item)
        if isinstance(item, classes.NeosDirectory) or item.name in exclude:
            loop = asyncio.get_event_loop()
            tasks.append(loop.create_task(printContents(item, indentation + 1, exclude=exclude)))
    if tasks:
        await asyncio.wait(tasks)
        for task in tasks:
            [objects.append(obj) for obj in task.result()]
    return objects


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
        try:
            await c.login(deets)
        except Exception as e:
            print(e)
            print("it seems that that login was invalid :(")
            exit(-1)
        data = input(
            f"Would you like to store your token to your harddrive? this token will expire naturally at {c.expirey}"
        )
        if data.lower() in ["true", "1", "t", "y", "yes", "yeah", "yup"]:
            print("saving token..")
            c.saveToken()

    est = await printContents(
        await c.resolveLink(next(x for x in await c.getInventory() if x.name == "Essential Tools"))
    )
    # todo: more stuff here
    print("content from essential Tools:")
    print(Counter([z.lastModifyingUserId for z in est]).most_common())

    neosess = await printContents(
        await c.resolveLink(next(x for x in await c.getInventory() if x.name == "Neos Essentials"))
    )
    # todo: more stuff here
    print("content from Neos Essentials:")
    print(Counter([z.lastModifyingUserId for z in neosess]).most_common())


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
