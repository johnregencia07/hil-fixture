test: test_protocol
	./test_protocol

test_protocol: test_protocol.c ../main/protocol.c ../main/protocol.h
	gcc -std=c99 -Wall -Wextra -Werror -I../main test_protocol.c ../main/protocol.c -o test_protocol

clean:
	rm -f test_protocol
