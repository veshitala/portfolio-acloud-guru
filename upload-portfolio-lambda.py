import boto3
from botocore.client import Config
from io import StringIO
import io
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:369122962402:deployPortFolioTopic')
    location = {"bucketName":"portfolio.future-eps.ml" , "objectKey":'portfoliobuild.zip'}
    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"]=="MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print("Building portflio from" + str(location))
        s3 = boto3.resource('s3' ,config = Config(signature_version = 's3v4'))

        portfolio_bucket  = s3.Bucket('portfolio.future-eps.ml')
        build_bucket  = s3.Bucket(location["bucketName"])

        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj , nm , ExtraArgs = {'ContentType' : mimetypes.guess_type(nm)[0]} )
                portfolio_bucket.Object(nm).Acl().put(ACL = 'public-read')

        print('job done')
        topic.publish(Subject = "portfolio deployed" , Message = "portfolio deployed successfully")
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId = job["id"])
    except:
        topic.publish(Subject = 'deployement failed' , Message  = "something went wrong")
        raise
    return 'Hello from Lambda'
