IF S:FS THEN		(* this is the first, normal scan of the routines in the current program. *)
	ThresTemp:=30;
	TON.PRE:=3000;
	TON.Reset:=0;
	TON.DN:=0;

	ButtonLevel1:= 0;
	ButtonLevel2:= 0; (* Button for level 2 to go down *)
	currentLevel:= 1; (* 1 for level 1 and 2 for level 2 *)
	moving:=0; (* True if the elevator is moving *)
	doorOpen:=0; (* True if the door is open *)
	doorOpening:=0;
	doorClosing:=0;

	fireAlarm:=0; (* True if fire alarm is active *)
	weight:= 0; (* Weight sensor reading *)

	movingToLevel1:=0;
	movingToLevel2:=0;
	MAX_WEIGHT := 1200;
	MAX_TEMP := 26;
	DO_00 := 0;
	DO_01 := 0;
	DO_02 := 0;
	DO_03 := 0;
	DO_00 := 0;
	DO_05 := 0;
	DO_06 := 0;
	DO_07 := 0;
	DO_08 := 0;
	DO_01 := 0;
	DO_00 := 0;
	DO_11 := 0;
END_IF;


TON.Reset := 0;

IF DI_08 THEN
	weight := 800;
END_IF;

IF DI_09 THEN
	weight := 1300;
END_IF;

IF Temp1 > MAX_TEMP THEN
	fireAlarm := 1;
	DO_11 := 1; // used to indicate fire alarm
ELSE
	fireAlarm := 0;
	DO_11 := 0;
END_IF;

IF doorOpen THEN
	doorOpening := 0;
	doorClosing := 0;
END_IF;

IF doorOpening THEN
	doorOpen := 0;
END_IF;

IF doorClosing THEN
	doorOpen := 0;
END_IF;

IF moving THEN
	DO_00 := 1; // Used to indicate door is openned
ELSE
	DO_00 := 0;
END_IF;

IF doorOpen THEN
	DO_08 := 1; // Used to indicate door is openned
ELSE
	DO_08 := 0;
END_IF;

IF doorOpening THEN
	DO_01 := 1; // Used to indicate door is opening
ELSE
	DO_01 := 0;
END_IF;

IF doorClosing THEN
	DO_03 := 1; // Used to indicate door is closing
ELSE
	DO_03 := 0;
END_IF;

IF movingToLevel1 THEN
	DO_06 := 1; // Used to indicate the elevator is moving down
ELSE
	DO_06 := 0;
END_IF;

IF movingToLevel2 THEN
	DO_02 := 1; // Used to indicate the elevator is moving down
ELSE
	DO_02 := 0;
END_IF;

IF currentLevel = 1 THEN
	DO_07 := 1;
	DO_03 := 0;
ELSE
	DO_07 := 0;
	DO_03 := 1;
END_IF;


IF doorOpening THEN  // If the door is opening, then we wait the door to open
    IF TON.DN THEN
		TON.Reset := 1;
		TONR(TON);
        doorOpening := 0;
        doorOpen := 1;
        IF NOT(fireAlarm) THEN // if no fire alarm is triggered, we start the door open timer and close after timer
            TON.TimerEnable := 1;
        END_IF;
    END_IF;
END_IF;

IF doorClosing THEN // if the door is closing, we wait until the door get's closed. Then if require the elevator to move, start moving it.
    IF TON.DN THEN
		TON.Reset := 1;
		TONR(TON);
        doorClosing := 0;
        doorOpen := 0;
        IF movingToLevel1 OR movingToLevel2 THEN
            moving := 1;
        END_IF;
    END_IF;
END_IF;

IF doorClosing AND fireAlarm THEN
	doorClosing := 0;
END_IF;

IF NOT(fireAlarm) AND doorOpen THEN // if the door is openned and no fire alarm, then we wait after the timer expire and close the door
	IF weight > MAX_WEIGHT THEN
		DO_08 := 1;
	ELSE
		DO_08 := 0;
		IF TON.DN THEN
			TON.Reset := 1;
			TONR(TON);
        	doorClosing := 1;
        	doorOpen := 0;
			TON.TimerEnable := 1;
    	END_IF;
	END_IF;
END_IF;

IF moving THEN
	IF TON.DN THEN
		TON.Reset := 1;
		moving := 0;
		doorOpening := 1;
		TON.TimerEnable := 1;
		IF movingToLevel1 THEN
			currentLevel:=1;
			movingToLevel1 := 0;
		ELSE
			currentLevel:=2;
			movingToLevel2 := 0;
		END_IF;
	END_IF;
	IF fireAlarm THEN
		movingToLevel1 :=1;
		TON.Reset := 1;
		TONR(TON);
		TON.TimerEnable := 1;
	END_IF;
ELSE
	IF fireAlarm THEN
		IF NOT(doorOpening) AND NOT(doorOpen) THEN  // Here
			doorOpening := 1;
			doorClosing := 0;
			TON.Reset := 1;
			TONR(TON);
			TON.TimerEnable := 1;
		END_IF;
	ELSIF NOT(doorOpen) AND NOT(doorOpening) THEN
		IF DI_03 THEN
			IF currentLevel <> 2 THEN
				movingToLevel2 := 1;
				moving := 1;
				TON.Reset := 1;
				TONR(TON);
				TON.TimerEnable := 1;
			ELSE
				movingToLevel1 := 1;
				doorOpening := 1;
				TON.Reset := 1;
				TONR(TON);
				TON.TimerEnable := 1;
			END_IF;
		ELSIF DI_07 THEN
			IF currentLevel <> 1 THEN
				movingToLevel1 := 1;
				moving := 1;
				TON.Reset := 1;
				TONR(TON);
				TON.TimerEnable := 1;
			ELSE
				movingToLevel2 := 1;
				doorOpening := 1;
				TON.Reset := 1;
				TONR(TON);
				TON.TimerEnable := 1;
			END_IF;
		END_IF;
	END_IF;
END_IF;
TONR(TON);
