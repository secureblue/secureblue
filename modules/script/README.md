# `script` module for startingpoint

The `script` module can be used to run arbitrary scripts at image build time that take no or minimal external configuration (in the form of command line arguments).
The scripts, which are run from the `config/scripts` directory, are declared under `scripts:`.

```yml
type: script
scripts:
    - signing.sh 
```