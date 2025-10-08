# app/middleware/security.py
import time
from typing import Dict

from fastapi import Request, HTTPException


class RateLimitMiddleware:

    def __init__(self):
        self.attempts: Dict[str, list] = {}
        self.max_attempts = 5
        self.window_minutes = 15

    async def __call__(self, request: Request, call_next):
        if request.url.path == "/profil/password/request-change":
            client_ip = request.client.host
            current_time = time.time()

            if client_ip in self.attempts:
                self.attempts[client_ip] = [
                    attempt_time for attempt_time in self.attempts[client_ip]
                    if current_time - attempt_time < self.window_minutes * 60
                ]

            if client_ip in self.attempts and len(self.attempts[client_ip]) >= self.max_attempts:
                raise HTTPException(
                    status_code=429,
                    detail=f"Trop de tentatives de changement de mot de passe. Réessayez dans {self.window_minutes} minutes."
                )

            if client_ip not in self.attempts:
                self.attempts[client_ip] = []
            self.attempts[client_ip].append(current_time)

        response = await call_next(request)
        return response
