# TimeJumpers

Time jumper was created as a one-stop application to help you navigate faster. We give users the ability to log in and upload local videos or specify links of videos stored within AWS or google cloud storage. Our users can then search for keywords and click on the results to navigate or “JUMP” through the video.

## Cloud Architecture Diagram
![Image of Cloud Architecture](https://github.com/mcbridemarci/TimeJumpers/images/Arch2.png)

## Application Architecture Diagram 
![Image of Application Architecture](https://github.com/mcbridemarci/TimeJumpers/images/Arch1.png)

## Process Flow Diagram 
![Image of Process Flow](https://github.com/mcbridemarci/TimeJumpers/images/Arch3.png)

## Environment Setup 

```
git clone https://github.com/mcbridemarci/TimeJumpers.git
cd TimeJumpers
python3 venv timejumperenv
source timejumperenv/bin/activate
pip3 install -r requirements.txt
python3 manage.py runserver 0.0.0.0:8000
```

## Amazon EC2 Setup 

```
Navigate to EC2 Dashboard in the AWS console
Launch Instance
Choose AMI [In our case, we selected Windows server, as we wanted to run our Django server on this OS.]
Select Memory, CPU
Choose number of instances, if we want auto scaling [load balancing], 
Select amount of storage
Add security groups [Includes VPC, subnet]
Launch Instance
Connect to EC2 instance by logging into RDP.
```

## Amazon RDS Setup 

```
Navigate to RDS Dashboard in the AWS console
Create Database
Choose easy create
Choose PostgreSql 
Launch database
Add Security group for database such that it is accessible only from the EC2.[snapshot shared in next slides]
Install Pgadmin to view your data locally as you will not be able to query data from the AWS console. 
```

### Authors 
Jeffrey McIntosh 
Marci McBride
Akshaya Kumar 
Sukarma Parimoo  