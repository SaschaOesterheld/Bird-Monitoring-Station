Project needs python3.11.2
	If other python version on current RaspianOS install pyenv:
		sudo apt update
		sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev tk-dev wget curl
		curl https://pyenv.run | bash
		nano ~/.bashrc
			#Add to end of the file
			export PYENV_ROOT="$HOME/.pyenv"
			export PATH="PYENV_ROOT/bin:$PATH"
			eval "$(pyenv init --path)"
			eval "$(pyenv init -)"
			#Save and exit file
		source ~/.bashrc
		#verify pyenv is working
		pyenv --version
		#get python3.11.2
		pyenv install 3.11.2
		#set python version for project
		cd "your project directory"
		pyenv local 3.11.2


		#make environment 
		python -m venv venv
		#activate venv
		source venv/bin/activate
		#install HDF5 for tensorflow and PortAudio for USB Mics
		sudo apt install -y libhdf5-dev hdf5-tools
		sudo apt install -y libportaudio2 portaudio19-dev
		#get the rest from requirements.txt(this may take a while, if >1h somethings is wrong)
		pip install -r requirements.txt

		#enable i2c in system settings
		sudo raspi-config
		sudo raspi-config nonint do_i2c 0 (für BME!)
		#enable I2C under the Interface Rider there
	
