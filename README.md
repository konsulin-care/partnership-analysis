**Installation:**

```bash
conda env create -f environment.yml
conda activate partnership-analysis
pip install -e .
```

**Update:**

```bash
conda env update -f environment.yml --prune
```

**Continuous Integration:**

This project uses GitHub Actions for automated testing. Tests are run on every pull request to the `master` branch using pytest.
