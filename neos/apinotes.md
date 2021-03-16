get invenhtory base

`api/users/UID/record?path=Inventory`

get Link Details: https://cloudx.azurewebsites.net/api/users/U-ItsDusty/records/R-7834919f-a45d-44c5-a513-f925de70f557


from link, get owner, record id;

`api/users/{Owner}/{record}`

from the link details,
`api/users/{owner}/record?path={the above's result's path}`