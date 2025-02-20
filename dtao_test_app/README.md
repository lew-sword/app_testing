# Macrocosmos dTao App
A lightweight app that can be used to demonstrate how python code can be displayed using streamlit

## Installation 
- Download the `config.toml`, `macro_dtao_app.py` and `env.yml` files, and save to a directory.
- Open that directory in terminal and then run 

    `conda env create -f env.yml`

- This will provide the necessary packages. As of writing this, bittensor dTao is not launced and version `9.0.0rc2` is being used here.
- Activate the envrioment with 

    `conda activate macrocosmos-dtao-app`
- Run in terminal 

    `streamlit run macro_dtao_app.py` 

- The app should open in a new window and begin populating the data tables. The chart will take time to load due to bittensor rate limit.