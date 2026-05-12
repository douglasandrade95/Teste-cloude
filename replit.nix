{ pkgs }: {
    deps = [
        pkgs.python311
        pkgs.python311Packages.pip
        pkgs.nodejs_20
        pkgs.ffmpeg
        pkgs.libsm
        pkgs.libxext
        pkgs.xorg.libX11
        pkgs.libxrender
    ];
}
