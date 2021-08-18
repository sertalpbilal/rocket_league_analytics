FROM ubuntu:latest

RUN apt-get update
RUN apt install -y python3 python3-pip wget

RUN pip install carball numpy==1.20.3 requests python-dotenv ipykernel xgboost scikit-learn progress wrapt_timeout_decorator matplotlib tabulate astropy colorama
RUN pip install boxcars-py --upgrade

WORKDIR /app/src

CMD python3 replay.py && python3 convert.py && cd xg_model && python3 -c "from score import convert_all; convert_all()" && cd .. && python3 csv_trimmer.py && python3 boxcarstest.py
# && python3 boxcars_dev.py
# CMD python3 replay.py && python3 convert.py

# CMD ls /data && cd /data/replay && carball -i 1ab1006e-f6f3-43bb-9f67-1d0de8b2f720.replay --json 1ab1006e-f6f3-43bb-9f67-1d0de8b2f720.json