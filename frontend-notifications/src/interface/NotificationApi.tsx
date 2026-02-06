export default interface NotificationApi {
  id: number;
  ticket_id: string;
  message: string;
  sent_at: string;
  read: boolean;
}
