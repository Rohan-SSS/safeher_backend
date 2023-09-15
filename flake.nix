{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
    devenv.url = "github:cachix/devenv/v0.6.3";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    devenv,
    poetry2nix,
    ...
  } @ inputs: let
    inherit (poetry2nix.legacyPackages."x86_64-linux") mkPoetryEnv overrides;
    pkgs = nixpkgs.legacyPackages."x86_64-linux";

    pythonEnv = mkPoetryEnv {
      # python = pkgs.python39;
      projectDir = ./.;
      overrides = overrides.withDefaults (final: prev: {
        tiktoken = prev.tiktoken.override {
          preferWheel = true;
        };

        langsmith = prev.langsmith.override {
          preferWheel = true;
        };

        numpy = prev.numpy.override {
          preferWheel = true;
        };

        unstructured = prev.unstructured.override {
          preferWheel = true;
        };

        pinecone-client = prev.pinecone-client.override {
          preferWheel = true;
        };
      });
      # preferWheels = true;
    };
    devshell = devenv.lib.mkShell {
      inherit inputs pkgs;
      modules = [
        {
          services.postgres.enable = true;
          services.postgres.listen_addresses = "127.0.0.1";
          services.postgres.initialDatabases = [
            {name = "womenProtection";}
          ];
        }
      ];
    };
  in {
    devShell.x86_64-linux = pkgs.mkShell {
      buildInputs = [pythonEnv];
      packages = [
        poetry2nix.packages."x86_64-linux".poetry
        devshell
      ];
    };
  };
}
