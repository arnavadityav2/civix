import React from 'react';
import { 
  User, 
  Building2, 
  Smartphone, 
  Phone, 
  Car, 
  CreditCard, 
  Fingerprint, 
  ShieldCheck 
} from 'lucide-react';

export type EntityType = 
  | 'PERSON' 
  | 'ORGANIZATION' 
  | 'DEVICE' 
  | 'PHONE_NUMBER' 
  | 'VEHICLE' 
  | 'FINANCIAL_ACCOUNT' 
  | 'SOURCE_IDENTITY'
  | string;

interface EntityAvatarProps {
  entityType?: EntityType;
  avatarUrl?: string | null;
  name?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl';
  className?: string;
}

const ENTITY_ICONS: Record<string, React.ElementType> = {
  PERSON: User,
  ORGANIZATION: Building2,
  DEVICE: Smartphone,
  PHONE_NUMBER: Phone,
  VEHICLE: Car,
  FINANCIAL_ACCOUNT: CreditCard,
  SOURCE_IDENTITY: Fingerprint,
};

const ENTITY_ICON_COLOR: Record<string, string> = {
  PERSON: 'text-civix-blue-400',
  ORGANIZATION: 'text-civix-gold-400',
  DEVICE: 'text-civix-blue-300',
  PHONE_NUMBER: 'text-civix-green-400',
  VEHICLE: 'text-civix-red-400',
  FINANCIAL_ACCOUNT: 'text-civix-gold-400',
  SOURCE_IDENTITY: 'text-civix-text-secondary',
};

const ENTITY_ICON_BORDER: Record<string, string> = {
  PERSON: 'bg-civix-blue-950 border-civix-blue-600/50',
  ORGANIZATION: 'bg-civix-gold-950 border-civix-gold-600/50',
  DEVICE: 'bg-civix-surface-2 border-civix-blue-500/40',
  PHONE_NUMBER: 'bg-civix-green-950 border-civix-green-600/50',
  VEHICLE: 'bg-civix-red-950 border-civix-red-600/50',
  FINANCIAL_ACCOUNT: 'bg-civix-gold-950 border-civix-gold-600/50',
  SOURCE_IDENTITY: 'bg-civix-surface-2 border-civix-border',
};

const SIZE_CLASSES = {
  sm: 'w-6 h-6',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
  '2xl': 'w-24 h-24',
  '3xl': 'w-32 h-32',
};

const ICON_SIZES = {
  sm: 'w-3.5 h-3.5',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
  '2xl': 'w-12 h-12',
  '3xl': 'w-16 h-16',
};

/**
 * Universal EntityAvatar component.
 * Guarantees "SAME PERSON -> SAME IMAGE" across the application.
 */
export const EntityAvatar: React.FC<EntityAvatarProps> = ({ 
  entityType = 'OTHER', 
  avatarUrl, 
  name,
  size = 'md',
  className = ''
}) => {
  const type = entityType?.toUpperCase() || 'OTHER';
  
  // 1. If it's a person and we have an image, render the actual image.
  // This explicitly honors the existing photo mapping mechanism.
  if (type === 'PERSON' && avatarUrl) {
    return (
      <div className={`flex-shrink-0 rounded-sm overflow-hidden border border-civix-blue-600/30 ${SIZE_CLASSES[size]} ${className}`}>
        <img 
          src={avatarUrl} 
          alt={name || 'Person Identity'} 
          className="w-full h-full object-cover"
        />
      </div>
    );
  }

  // 2. Otherwise, render the universal CIVIX icon for the entity type
  const Icon = ENTITY_ICONS[type] || ShieldCheck;
  const borderClass = ENTITY_ICON_BORDER[type] || 'bg-civix-surface border-civix-border';
  const colorClass = ENTITY_ICON_COLOR[type] || 'text-civix-text-secondary';
  
  return (
    <div className={`flex-shrink-0 flex items-center justify-center rounded-sm border shadow-sm ${borderClass} ${SIZE_CLASSES[size]} ${className}`}>
      <Icon className={`${ICON_SIZES[size]} ${colorClass}`} />
    </div>
  );
};
