# Set Up Client Side
- Make a cli interface to handle user requests/interactions

# Finish Server Side
- Message Class
    - Message ID
    - Sender
    - Post Date
    - Subject

- User Class
    - connection time
    - username
    - group membership list

- Group (bb) class
    - List of messages recieved previously (and the metadata with those messages)
    - List of currently connected users

# Communication Protocol

Socket Send:
number body

Server Command Format:
```json
{
    command: "command goes here"
    /* command must be in the set:
    [
        join
        post
        users
        leave
        message
        exit
        groups
        groupjoin
        grouppost
        groupusers
        groupleave
        groupmessage
    ]
    */
    args:
    {
        // args go here
    }
}
```