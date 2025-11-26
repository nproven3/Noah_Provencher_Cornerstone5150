/*
    This program is designed to connect to a netcat session
    And just send messages.
    To get the connections after each on esend one back from
    The netcat server and a response will be displayed from both
    The client and the server.
*/

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>


struct sockaddr_in srv;

ssize_t ClientSend(int d, const void *buffer, size_t length)
{
    char *temp = (char *)buffer;
    size_t R_buffer = length;
    while (R_buffer > 0)
    {
        ssize_t n = send(d, temp, R_buffer, 0);
        if(n > 0)
        {
            temp += (size_t)n;
            R_buffer -= (size_t)n;
            continue;
        }

        if(n == 0)
        {
            return 0;
        }
        
        if(errno == EINTR)
        {
            continue;
        }
        return -1;
    }
    return (ssize_t)length;
}

int main()
{

    char * host = "127.0.0.1";
    int port = 5555;
    int Socket = -1;

    Socket = socket(AF_INET, SOCK_STREAM, 0);
    if(Socket < 0)
    {
        return 1;
    }

    //struct sockaddr_in srv; //Might not need this in the main function

    memset(&srv, 0, sizeof(srv));
    srv.sin_family = AF_INET;
    srv.sin_port = htons(port);
    if(inet_pton(AF_INET, host, &srv.sin_addr) != 1)
    {
        printf("failed\n");
        return 1;
    }

    if(connect(Socket, (struct sockaddr*)&srv, sizeof(srv)) <0)
    {
        printf("Did not connect\n");

        return 1;
    }

    printf("Connected to %s, on port %d\n", host, port);

    char input[512];
    char response[2048];

    while(fgets(input, sizeof input, stdin) != NULL)
    {
        size_t length = strlen(input);
        if(length == 0)
        {
            continue;
        }

        ssize_t mSent = ClientSend(Socket, input, length);
        if(mSent < 0)
        {
            printf("Did not send messages\n");
            return 1;
        }

        if(mSent == 0)
        {
            printf("Connection Closed\n");
        }

        ssize_t receive = recv(Socket, response, sizeof(response) - 1, 0);

        if(receive < 0) 
        {
            printf("oof\n");
            return 1;
        }
        if(receive == 0)
        {
            printf("Server closed connection\n");
        }

        response[receive] = '\0';
        printf("%s\n", response);
        fflush(stdout);
    }

    close(Socket);

    return 0;
}