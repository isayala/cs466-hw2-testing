# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import boto3
import pandas as pd
import requests

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can say your course subject followed by the course number to find out what textbooks are required"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetRequiredTextbookIntentHandler(AbstractRequestHandler):
    """ Handler for Get Required Textbook Intent"""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetRequiredTextbookIntent")(handler_input)

    def handle(self, handler_input):

        # Extract slot values from the intent
        try:
            slots = handler_input.request_envelope.request.intent.slots
            course_subject_abbreviation = slots['course_subject_abbreviation'].value
            course_number = int(slots['course_number'].value)
            professor_name = slots['professor_name'].value if 'professor_name' in slots else None
            course_subject = None

            # CSV is going to have capitalized letters so we need alter the input to match

            if course_subject_abbreviation is not None:
                if len(course_subject_abbreviation) > 4:
                    course_subject = course_subject_abbreviation.capitalize()
                    course_subject_abbreviation = None
                else:
                    course_subject_abbreviation = course_subject_abbreviation.upper()

        # We have the slots as required so we know we have the information we need so no validation is needed
        # Read the CSV file
            df = pd.read_csv('textbooks.csv')
            output = "I'm sorry, I couldn't find the required textbooks for the course you requested."

            if course_subject is not None:
                result = df[(df['course_number'].eq(course_number)) & (df['course_subject'].eq(course_subject))]
            else:
                result = df[(df['course_number'].eq(course_number)) & (df['course_subject_abbreviation'].eq(course_subject_abbreviation))]
                

            if result.shape[0] == 0:
                return (
                    handler_input.response_builder.speak(output)
                        .set_should_end_session(True)
                        .response
                )
            
            # get the first row and return the name of the course and the required textbooks
            course_info = result.iloc[0]

            output = f"The required textbooks for {course_info['course_subject']} {course_info['course_number']} are: {course_info['required_textbook']}"
        except Exception as e:
            output = "Error: {}".format(str(e))

        return (
            handler_input.response_builder.speak(output)
                .set_should_end_session(True)
                .response
        )
        
    
class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        sts_client = boto3.client('sts')

        assumed_role_object = sts_client.assume_role(RoleArn="arn:aws:iam::211125677796:role/alexaskills",
                                                     RoleSessionName="AssumeRoleSession1")
        credentials = assumed_role_object['Credentials']

        dynamodb = boto3.resource('dynamodb',
                                  aws_access_key_id=credentials['AccessKeyId'],
                                  aws_secret_access_key=credentials['SecretAccessKey'],
                                  aws_session_token=credentials['SessionToken'],
                                  region_name='us-west-2')

        try:
            table = dynamodb.Table('textbookalexa')
            response = table.scan()
            items = response['Items'][:10]  # Extract first 10 items
            output = "First 10 rows:\n"
            for item in items:
                output += str(item) + "\n"  # Format each item as a string and append to output
        except Exception as e:
            output = "Error: {}".format(str(e))  # Handle exception

        return (
            handler_input.response_builder.speak(output)
                .set_should_end_session(True)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetRequiredTextbookIntentHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()