# One documented inherited-test supersession

Run 35822192132 executed all 217 baseline cases on exact unchanged 2103229: 210 passed, all six intended runtime regression proofs reproduced as their expected assertions, and one legacy test failed because its expectation predates an approved contract change. There were no missing or skipped cases.

`Cobra2103179BufferResilienceTest.localPlaylistStartsWithNineSecondReserve` asserted a 9-second local playlist reserve. `repairs/cobra-playback-finalization-2103180/apply.py` explicitly changed that exact field to 15 seconds. The 2103181 and 2103182 tests already assert the 15-second live reserve (and distinct 21-second startup reserve), and passed on 2103229. The protected source continues to contain `TIME-OFFSET=-15.0,PRECISE=NO`.

Only the copied test fixture's obsolete literal is changed from 9 to 15; its historical method identity and all other assertions remain unchanged. The original repository test and all production timeshift code remain untouched. The same adapted fixture is used against both parent and candidate, with original and compiled fixture hashes and the reason logged in each phase's fixture.json. No test is deleted or skipped. The six new regression proofs themselves remain byte-identical between red and green phases.

The raw failed baseline run remains available as evidence and is not reclassified as a passing build.
