export default class WebSocketManager {
  constructor(url, callbacks = {}) {
    this.url = url;
    this.callbacks = callbacks;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;

    this.connect();
  }

  connect() {
    try {
      this.socket = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      this.handleReconnect();
    }
  }

  setupEventHandlers() {
    this.socket.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
      this.callbacks.onOpen?.();
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected");
      this.callbacks.onClose?.();
      this.handleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.callbacks.onError?.(error);
    };
  }

  handleMessage(message) {
    console.log("WebSocket message received:", message);
    const handler = this.callbacks[message.type];
    if (handler) {
      handler(message);
    } else {
      console.warn("No handler for message type:", message.type);
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnection attempt ${this.reconnectAttempts}`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket not connected, cannot send data");
    }
  }
}
