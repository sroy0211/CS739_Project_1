# CS739_Project_1 
Make your own environment and install desired packages as instructed in the Canvas webpage, there is a documentation given on installing libraries for grpc, etc, then make a seperate branch for pushing the code in order to run the python codes.

Server terminal commands

python3 server.py

CLient terminal commands

python3 client_library.py put name "Souvik Roy" --timeout 5 --wait 3
python3 client_library.py get name --timeout 5

Client Arguments

parser.add_argument('operation', choices=['get', 'put'], help='Specify whether to get or put')
parser.add_argument('key', help='The key for the GET/PUT operation')
parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
parser.add_argument('--server', default="localhost:50051", help='Server address (default: localhost:50051)')
parser.add_argument('--timeout', type=int, default=0, help='Timeout for the GET operation to terminate in case of server failure/crash (in seconds)')
parser.add_argument('--wait', type=int, default=0, help='Time to wait between PUT and GET operations (in seconds)')
