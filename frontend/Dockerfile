FROM node:3.16-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install --production
COPY frontend .
ENV Backend_API_URL=publicip:8000/api
EXPOSE 3000
ENTRYPOINT [ "npm" ]
CMD [ "start" ]