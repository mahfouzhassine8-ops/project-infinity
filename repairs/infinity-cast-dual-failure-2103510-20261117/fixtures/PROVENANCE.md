Synthetic testsrc2 video and sine audio,12.02seconds,320x180/24fps, genuine x265 Main10 Level5.1 SDR709 and E-AC3. Explicit encoder VUI colorprim=1:transfer=1:colormatrix=1; Main10 is not treated as HDR.

make_inband_fixture.py remuxes real parameter sets using FFmpeg hevc_mp4toannexb with write_crc32=0, replaces only out-of-band arrays with same-length EBML Void, and turns later duplicate parameter NALs into valid same-length filler. VCL bytes, packet layout, cues and timestamps remain intact. Full decoded A/V frame hashes and times match the control. Source/private codec metadata is never fabricated by production.

Fixtures are generated media, not owner recordings or provider sources. No physical hardware/TV claim. The earlier handwritten short-fixture prototype is historical and is not used for current CI.
