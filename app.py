import os
import base64
import datetime

from flask import Flask, jsonify, request
import jwt


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = os.getenv('secret') or 'super-secret'


def token_required(func):
    def wrapper():
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            data = jwt.decode(
                jwt=token, key=app.config['SECRET_KEY'], algorithms=['HS256'])
            if data['expires'] < datetime.datetime.utcnow().timestamp():
                raise jwt.ExpiredSignatureError
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            return jsonify({'message': 'Token is invalid!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token is expired!'}), 403

        return func()
    return wrapper


@app.route('/unprotected')
def unprotected():
    return 'Hello'


@app.route('/auth')
def auth():
    current_timestamp = datetime.datetime.utcnow()
    expires = current_timestamp + datetime.timedelta(minutes=30)

    headers = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'host': request.headers.get(
        'Host'), 'expires': expires.timestamp()}

    token = jwt.encode(headers=headers, payload=payload,
                       key=app.config['SECRET_KEY'])

    return jsonify({'token': token})


@app.route('/protected')
@token_required
def protected():
    image_path = os.path.join('mustang.jpg')
    encoded_image = ''

    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())

    return jsonify({
        'timestamp': datetime.datetime.utcnow().timestamp(),
        'message': 'Token has been passed',
        'image': encoded_image.decode('utf-8')
    })


if __name__ == '__main__':
    app.run(debug=True)
