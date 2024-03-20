with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    zola
  ];
  shellHook = ''
    alias c=clear
    alias m=make
  '';
}