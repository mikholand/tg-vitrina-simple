import type { ContactType } from './types'

export const contactTypeLabels: Record<ContactType, string> = {
  telegram: 'Telegram',
  phone: 'Телефон',
}

export const contactTypeIcons: Record<ContactType, string> = {
  telegram: 'pi-telegram',
  phone: 'pi-phone',
}

export const contactTypeValueLabels: Record<ContactType, string> = {
  // «Аккаунт в Telegram», не «Имя пользователя» — рядом в форме уже есть
  // поле «Имя менеджера», и два «имени» подряд читались бы как одно и то же.
  telegram: 'Аккаунт в Telegram',
  phone: 'Номер телефона',
}

export const contactTypeValuePlaceholders: Record<ContactType, string> = {
  telegram: '@username',
  phone: '+7 999 000-00-00',
}
