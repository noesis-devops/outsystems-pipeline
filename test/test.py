import sys
import os
sys.path.append("C:\\Users\\dmc\\Documents\\github")
sys.path.append("C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline")
sys.path.append("C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems")
sys.path.append(os.getcwd())

if __name__ == "__main__":

    # call = r"C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems\\pipeline\\fetch_apps_source_code.py --artifacts {} --lt_url {} --lt_token {} --lt_api_version {} --target_env {} --app_list {} --inc_pattern {} --exc_pattern {}".format(args["artifacts_folder"], args["lt_url"], args["lt_token"], args["lt_version"], args["target_env"], args["app_list"], args["inc_pattern"], args["exc_pattern"])
    os.environ["OS_PIPELINE_CONFIG_FILE"] = "test\\conf.properties"

    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg0ZjgwZTdmLTI1NjItNDUxOC1iNDU5LTY2MjU0YWQwMTBjMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjkwODk5NzAzIiwic3ViIjoiTmpOaVl6WXpNV0V0TjJGa01TMDBZell3TFdJNU1EY3RZVEEyTlRGaVlXRmtOalk0IiwianRpIjoiWjdIWEdIc3lKTCIsImV4cCI6MTc1NDA1ODEwMywiaXNzIjoibGlmZXRpbWUiLCJhdWQiOiJsaWZldGltZSJ9.lQPEWVsMj3VB0qGPesTVYGvJROkn6--KTWo4Fb_ZO6afLpLMLL214u9UISijJaMXj19vjDNpjlBZW-ggnQ3lTiEn8iHy7LmCLb_ODF1TqdoTfJBTbpUbpTAcqDxbd0CGf5u2oDyUS6sNz9kwNlk40pNdXCXhD6sud9WRu9qDvg2fgDt1Z69V8CHmNhssyGga9VIsYx_wMJ9lGfMy40kyXu5RZg8uNeq-1RPErzZOwFCuUKsCdQigVAhQ9_fj_FmnXdRXL-hIjTCdcMCf9FV1v8f7Gs-t_0j5nMDAGi_qotxRXXGO4mT2xkJSRAcVWeOJMuTG26oN_S-pJlaVXASYYQ"
    # call = r"C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems\\configurations\\pipeline_configurations.py"

    # call = r"C:\\Users\\dmc\\Documents\\github\\outsystems-pipeline\\outsystems\\pipeline\\increment_app_tags.py  --artifacts test\\Artifacts --lt_url showcase-lt.outsystemsdevopsexperts.com --lt_token {} --lt_api_version 2".format(token)
    # os.system(call)
    app_list = "Cases,Cases_Tests,CRM Services"
    ProbeEnvironmentURL = 'https://showcase-reg.outsystemsdevopsexperts.com/'

    #call = r'C:\Users\dmc\Documents\outsystems-cicd\outsystems-pipeline\outsystems\pipeline\fetch_apps_packages.py  --artifacts test\\Artifacts --lt_url showcase-lt.outsystemsdevopsexperts.com --lt_token {} --lt_api_version 2 --cicd_probe_url {} --source_env {} --app_list "{}" --generate_deploy_order --friendly_package_names'.format(token, ProbeEnvironmentURL, "Development", app_list)
    #os.system(call)


    manifest_file = r"C:\Users\dmc\Documents\outsystems-cicd\outsystems-pipeline\test\Artifacts\trigger_manifest.json"
    artifacts_folder = r"test\Artifacts"

    call = r'C:\\Users\\dmc\\Documents\\outsystems-cicd\\outsystems-pipeline\\outsystems\\pipeline\\deploy_oap_to_target_env.py --artifacts "{}" --lt_url showcase-lt.outsystemsdevopsexperts.com --lt_token {} --lt_api_version 2 --destination_env_label {} --manifest_file {} --include_test_apps --friendly_package_names'.format(artifacts_folder, token, "Regression", manifest_file)
    os.system(call)
