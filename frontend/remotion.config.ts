import { Config } from 'remotion';

Config.setVideoImageFormat('png');
Config.setCodecH264Preset('faster');
Config.setBitrate('8M');
Config.setFrameRange([0, 300]);
Config.setRange([0, 10]);
Config.setConcurrency(4);
Config.setMaxRetries(3);
Config.setEntryPoint('./src/remotion/Root');
