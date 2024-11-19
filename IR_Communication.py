from tdmclient import ClientAsync

seeker_program = """
var send_interval = 200  # time in milliseconds
timer.period[0] = send_interval

leds.top = [32, 0, 0]
leds.bottom.left = [32, 0, 0]
leds.bottom.right = [32, 0, 0]

call prox.comm.enable(1)
onevent timer0
    prox.comm.tx = 1
"""

avoider_program = """
var send_interval = 200  # time in milliseconds
timer.period[0] = send_interval
call prox.comm.enable(1)
leds.top = [0, 32, 0]

timer.period[0] = send_interval

onevent timer0
    prox.comm.tx = 2
    
onevent prox.comm
    if prox.comm.rx == 1 then
        leds.top = [32, 0, 32]
        leds.bottom.left = [32, 0, 32]
        leds.bottom.right = [32, 0, 32]
    end
    
"""

with ClientAsync() as client:
    with ClientAsync() as client:

        async def prog():
            """
            Asynchronous function controlling the Thymio.
            """

            # Lock the node representing the Thymio to ensure exclusive access.
            with await client.lock() as node:
                # Compile and send the program to the Thymio.
                error = await node.compile(seeker_program)
                if error is not None:
                    print(f"Compilation error: {error['error_msg']}")
                else:
                    error = await node.run()
                    if error is not None:
                        print(f"Error {error['error_code']}")

                # Wait for the robot's proximity sensors to be ready.
                await node.wait_for_variables({"prox.horizontal"})
                print("Thymio started successfully!")

                while True:
                    # get the values of the proximity sensors
                    prox_values = node.v.prox.horizontal

                    """
                    Get the value of the message received from the other Thymio
                    the value is 0 if no message has been received and 
                    gets set to a new value when a message is received" 
                    """

                    message = node.v.prox.comm.rx
                    print(f"message from Thymio: {message}")

                    if sum(prox_values) > 20000:
                        break

                    node.flush()  # Send the set commands to the robot.

                    await client.sleep(0.3)  # Pause for 0.3 seconds before the next iteration.

                # Once out of the loop, stop the robot and set the top LED to red.
                print("Thymio stopped successfully!")
                node.v.motor.left.target = 0
                node.v.motor.right.target = 0
                node.v.leds.top = [32, 0, 0]
                node.flush()


        # Run the asynchronous function to control the Thymio.
        client.run_async_program(prog)
