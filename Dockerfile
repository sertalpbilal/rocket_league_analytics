FROM ubuntu:latest

RUN apt-get update
RUN apt install -y python3 python3-pip

RUN pip install carball
RUN pip install requests
RUN pip install python-dotenv
RUN pip install ipykernel
RUN pip install xgboost
RUN pip install scikit-learn
RUN pip install progress
RUN pip install wrapt_timeout_decorator

WORKDIR /src

CMD python3 replay.py && python3 convert.py && cd xg_model && python3 -c "from score import convert_all; convert_all()" && cd .. && python3 csv_trimmer.py && python3 boxcarstest.py
# && python3 boxcars_dev.py
# CMD python3 replay.py && python3 convert.py

# CMD ls /data && cd /data/replay && carball -i 1ab1006e-f6f3-43bb-9f67-1d0de8b2f720.replay --json 1ab1006e-f6f3-43bb-9f67-1d0de8b2f720.json