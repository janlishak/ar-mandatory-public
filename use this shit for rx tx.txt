from tdmclient import ClientAsync

avoider_program = """
# Variables must be at start
var send_interval = 200  # time in milliseconds
var signal_detected = 0  # For storing received signal
var reset_delay = 500   # Reset after 500ms

# Enable communication first
call prox.comm.enable(1)

# Initialize timer
timer.period[0] = send_interval

# Set constant transmission
onevent timer0
    prox.comm.tx = 2  # Continuously send 2
    
# Force update rx value in every timer tick
    if prox.comm.rx == 0 then
        signal_detected = 0
    end

onevent prox.comm
    signal_detected = prox.comm.rx
    if signal_detected != 0 then
        timer.period[1] = reset_delay
    end

onevent timer1
    prox.comm.rx = 0  # Force reset rx
    signal_detected = 0
    timer.period[1] = 0
"""

seeker_program = """
# Variables must be at start
var send_interval = 200  # time in milliseconds
var signal_detected = 0  # For storing received signal
var reset_delay = 500   # Reset after 500ms

# Enable communication first
call prox.comm.enable(1)

# Initialize timer
timer.period[0] = send_interval

# Set constant transmission
onevent timer0
    prox.comm.tx = 1 # Continuously send 1
    
# Force update rx value in every timer tick
    if prox.comm.rx == 0 then
        signal_detected = 0
    end

onevent prox.comm
    signal_detected = prox.comm.rx
    if signal_detected != 0 then
        timer.period[1] = reset_delay
    end

onevent timer1
    prox.comm.rx = 0  # Force reset rx
    signal_detected = 0
    timer.period[1] = 0
"""

with ClientAsync() as client:
    async def prog():
        """
        Asynchronous function controlling the Thymio.
        """

        # Lock the node representing the Thymio to ensure exclusive access.
        with await client.lock() as node:
            # Compile and send the program to the Thymio.
            error = await node.compile(avoider_program)
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

                await client.sleep(1)  # Pause for 1 second

            # Once out of the loop, stop the robot and set the top LED to red.
            print("Thymio stopped successfully!")


    # Run the asynchronous function to control the Thymio.
    client.run_async_program(prog)