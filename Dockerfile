# use official python image
FROM python:3.12

# set working directory
WORKDIR /app

# copy requirements
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy project files
COPY . .

# expose flask port
EXPOSE 5000

# run flask app
CMD ["python", "src/app.py"]